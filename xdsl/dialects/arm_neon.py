from __future__ import annotations

from xdsl.dialects.arm.assembly import AssemblyInstructionArg
from xdsl.dialects.arm.register import ARMRegisterType
from xdsl.ir import (
    Dialect,
    EnumAttribute,
    SpacedOpaqueSyntaxAttribute,
    SSAValue,
    StrEnum,
)
from xdsl.irdl import (
    irdl_attr_definition,
)

ARM_NEON_INDEX_BY_NAME = {f"v{i}": i for i in range(0, 32)}


@irdl_attr_definition
class NEONRegisterType(ARMRegisterType):
    """
    A 128-bit NEON ARM register type.
    """

    name = "arm_neon.reg"

    @classmethod
    def instruction_set_name(cls) -> str:
        return "arm_neon"

    @classmethod
    def index_by_name(cls) -> dict[str, int]:
        return ARM_NEON_INDEX_BY_NAME

    @classmethod
    def infinite_register_prefix(cls):
        return "inf_"


UNALLOCATED_NEON = NEONRegisterType.unallocated()
V0 = NEONRegisterType.from_name("v0")
V1 = NEONRegisterType.from_name("v1")
V2 = NEONRegisterType.from_name("v2")
V3 = NEONRegisterType.from_name("v3")
V4 = NEONRegisterType.from_name("v4")
V5 = NEONRegisterType.from_name("v5")
V6 = NEONRegisterType.from_name("v6")
V7 = NEONRegisterType.from_name("v7")
V8 = NEONRegisterType.from_name("v8")
V9 = NEONRegisterType.from_name("v9")
V10 = NEONRegisterType.from_name("v10")
V11 = NEONRegisterType.from_name("v11")
V12 = NEONRegisterType.from_name("v12")
V13 = NEONRegisterType.from_name("v13")
V14 = NEONRegisterType.from_name("v14")
V15 = NEONRegisterType.from_name("v15")
V16 = NEONRegisterType.from_name("v16")
V17 = NEONRegisterType.from_name("v17")
V18 = NEONRegisterType.from_name("v18")
V19 = NEONRegisterType.from_name("v19")
V20 = NEONRegisterType.from_name("v20")
V21 = NEONRegisterType.from_name("v21")
V22 = NEONRegisterType.from_name("v22")
V23 = NEONRegisterType.from_name("v23")
V24 = NEONRegisterType.from_name("v24")
V25 = NEONRegisterType.from_name("v25")
V26 = NEONRegisterType.from_name("v26")
V27 = NEONRegisterType.from_name("v27")
V28 = NEONRegisterType.from_name("v28")
V29 = NEONRegisterType.from_name("v29")
V30 = NEONRegisterType.from_name("v30")
V31 = NEONRegisterType.from_name("v31")


class NeonArrangement(StrEnum):
    """
    The arrangement specifier for NEON instructions determines element size and count.
    We assume full 128-bit registers. Possible arrangements:
      - D  → 2 double-precision floats
      - S  → 4 single-precision floats
      - H  → 8 half-precision floats
    """

    D = "D"
    S = "S"
    H = "H"

    def map_to_num_els(self):
        map = {"D": 2, "S": 4, "H": 8}
        return map[self.name]


@irdl_attr_definition
class NeonArrangementAttr(EnumAttribute[NeonArrangement], SpacedOpaqueSyntaxAttribute):
    """
    Attribute containing the arrangement specification.
    """

    name = "arm_neon.arrangement"


class VectorWithArrangement(AssemblyInstructionArg):
    reg: NEONRegisterType | SSAValue
    arrangement: NeonArrangementAttr
    index: int | None = None

    def __init__(
        self,
        reg: NEONRegisterType,
        arrangement: NeonArrangementAttr,
        *,
        index: int | None = None,
    ):
        self.reg = reg
        self.arrangement = arrangement
        self.index = index

    def assembly_str(self):
        assert isinstance(self.reg, NEONRegisterType)
        if self.index is None:
            return f"{self.reg.register_name.data}.{self.arrangement.data.map_to_num_els()}{self.arrangement.data.name}"
        else:
            return f"{self.reg.register_name.data}.{self.arrangement.data.name}[{self.index}]"


ARM_NEON = Dialect(
    "arm_neon",
    [],
    [
        NeonArrangementAttr,
        NEONRegisterType,
    ],
)
