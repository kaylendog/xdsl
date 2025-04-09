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


@dataclass
class ConvertStoreOp(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: ptr.StoreOp, rewriter: PatternRewriter, /):
        rewriter.replace_matched_op(
            (
                cast_op := builtin.UnrealizedConversionCastOp.get(
                    (op.addr,), (llvm.LLVMPointerType.opaque(),)
                ),
                llvm.StoreOp(op.value, cast_op.results[0]),
            )
        )


@dataclass
class ConvertLoadOp(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: ptr.LoadOp, rewriter: PatternRewriter, /):
        rewriter.replace_matched_op(
            (
                cast_op := builtin.UnrealizedConversionCastOp.get(
                    [op.addr], [llvm.LLVMPointerType.opaque()]
                ),
                llvm.LoadOp(cast_op.results[0], op.res.type),
            )
        )


@dataclass
class ConvertPtrAddOp(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: ptr.PtrAddOp, rewriter: PatternRewriter, /):
        rewriter.replace_matched_op(
            (
                cast_addr_op := builtin.UnrealizedConversionCastOp.get(
                    [op.addr],
                    [llvm.LLVMPointerType.opaque()],
                ),
                # ptr -> int
                ptr_to_int_op := llvm.PtrToIntOp(
                    cast_addr_op.results[0], builtin.IndexType()
                ),
                # int + arg
                add_op := arith.AddiOp(ptr_to_int_op.results[0], op.offset),
                # int -> ptr
                llvm.IntToPtrOp(add_op.result),
            )
        )

        rewriter.erase_matched_op()


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
    Replaces `ptr_dxdsl.ptr` with `llvm.ptr`.
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
