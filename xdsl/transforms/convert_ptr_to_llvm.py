from dataclasses import dataclass

from xdsl.context import Context
from xdsl.dialects import arith, builtin, llvm, ptr
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    TypeConversionPattern,
    attr_type_rewrite_pattern,
    op_type_rewrite_pattern,
)
from xdsl.rewriter import InsertPoint


@dataclass
class ConvertStoreOp(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: ptr.StoreOp, rewriter: PatternRewriter, /):
        rewriter.insert_op(
            cast_op := builtin.UnrealizedConversionCastOp.get(
                [op.addr], [llvm.LLVMPointerType.opaque()]
            ),
            InsertPoint.before(op),
        )
        rewriter.replace_matched_op(llvm.StoreOp(op.value, cast_op.results[0]))


@dataclass
class ConvertLoadOp(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: ptr.LoadOp, rewriter: PatternRewriter, /):
        rewriter.insert_op(
            cast_op := builtin.UnrealizedConversionCastOp.get(
                [op.addr], [llvm.LLVMPointerType.opaque()]
            ),
            InsertPoint.before(op),
        )
        rewriter.replace_matched_op(llvm.LoadOp(cast_op.results[0], op.res.type))


@dataclass
class ConvertPtrAddOp(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: ptr.PtrAddOp, rewriter: PatternRewriter, /):
        # TODO: could be one cast?
        rewriter.insert_op(
            cast_addr_op := builtin.UnrealizedConversionCastOp.get(
                [op.addr],
                [llvm.LLVMPointerType.opaque()],
            ),
            InsertPoint.before(op),
        )
        rewriter.insert_op(
            cast_offset_op := arith.IndexCastOp(op.offset, builtin.i64),
            InsertPoint.before(op),
        )
        # TODO: pretending all pointees are f32s
        rewriter.replace_matched_op(
            llvm.GEPOp.from_mixed_indices(
                cast_addr_op.results[0],
                [cast_offset_op.result],
                pointee_type=builtin.f32,
            )
        )


class ReconcileUnrealizedPtrCasts(RewritePattern):
    """
    Eliminates `llvm.ptr` -> `llvm.ptr` casts.
    """

    @op_type_rewrite_pattern
    def match_and_rewrite(
        self, op: builtin.UnrealizedConversionCastOp, rewriter: PatternRewriter, /
    ):
        # preconditions
        if (
            len(op.inputs) != 1
            or len(op.outputs) != 1
            or not isinstance(op.inputs[0].type, llvm.LLVMPointerType)
            or not isinstance(op.outputs[0].type, llvm.LLVMPointerType)
        ):
            return

        # erase llvm.ptr -> llvm.ptr
        op.outputs[0].replace_by(op.inputs[0])
        rewriter.erase_matched_op()


class RewritePtrTypes(TypeConversionPattern):
    """
    asdf
    """

    @attr_type_rewrite_pattern
    def convert_type(self, typ: ptr.PtrType):
        return llvm.LLVMPointerType.opaque()


class ConvertPtrToLLVMPass(ModulePass):
    name = "convert-ptr-to-llvm"

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    ConvertStoreOp(),
                    ConvertLoadOp(),
                    ConvertPtrAddOp(),
                    RewritePtrTypes(),
                    ReconcileUnrealizedPtrCasts(),
                ]
            )
        ).rewrite_module(op)
