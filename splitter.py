import os
from ghidra.util.task import ConsoleTaskMonitor
from jarray import zeros
from ghidra.program.model.pcode import PcodeOp
from ghidra.program.model.block import BasicBlockModel

MAXIMUM_memoryOperations = 1
MIN_HANDLER = 1
HANDLER_SIZE = 500

def score_block(CurrentBlock, ProgramListing):
    #All variables for the most part near top of large logic areas
    IndirectBranching = False
    InstructionCount = 0
    MemoryOperations = 0
    BranchOperations = 0

    MaximumAddress = CurrentBlock.getMaxAddress()
    MinimumAddress = CurrentBlock.getMinAddress()

    CurrentInstruction = ProgramListing.getInstructionAt(MinimumAddress)
    while CurrentInstruction is not None and CurrentInstruction.getMinAddress() <= MaximumAddress:
        InstructionCount = InstructionCount + 1

        try:
            PcodeOperations = CurrentInstruction.getPcode()
        except:
            PcodeOperations = []

        for Operation in PcodeOperations:
            OperationCode = Operation.getOpcode()

            if OperationCode == PcodeOp.STORE or OperationCode == PcodeOp.LOAD:
                MemoryOperations = MemoryOperations + 1
            if OperationCode in ( #this gave so much trouble it's not even funny do not fhange
                PcodeOp.RETURN,
                PcodeOp.BRANCHIND,
                PcodeOp.CALLIND,
                PcodeOp.BRANCH,
                PcodeOp.CBRANCH,
                PcodeOp.CALL,
            ):
                BranchOperations = BranchOperations + 1
            if OperationCode == PcodeOp.CALLIND or OperationCode == PcodeOp.BRANCHIND:
                IndirectBranching = True

        CurrentInstruction = CurrentInstruction.getNext()

    return MemoryOperations, BranchOperations, IndirectBranching, InstructionCount


CurrentProgramObject = currentProgram
if CurrentProgramObject is None:
    print "No program"
    raise SystemExit

FunctionManager = CurrentProgramObject.getFunctionManager()
ProgramMemory = CurrentProgramObject.getMemory()
ProgramListing = CurrentProgramObject.getListing()

OutputDirectory = os.path.join(os.path.expanduser("~"), "SyntiaCandidates")
HomeDirectory = os.path.expanduser("~")

try:
    if not os.path.exists(OutputDirectory):
        os.makedirs(OutputDirectory)
        print "Created"
    else:
        print "Exists"
except Exception:
    print "Failed"
    raise SystemExit

RankingEntries = []
IndexLines = []

RankingFilePath = os.path.join(OutputDirectory, "ranking_by_score.txt")
IndexFilePath = os.path.join(OutputDirectory, "index.txt")



TaskMonitor = ConsoleTaskMonitor()
BasicBlockModelObject = BasicBlockModel(CurrentProgramObject)
BasicBlocks = BasicBlockModelObject.getCodeBlocks(TaskMonitor)

TotalBlocks = 0
BlockIdentifier = 0
SavedBlocks = 0
print "Start"

while BasicBlocks.hasNext() and not TaskMonitor.isCancelled():
    CurrentBlock = BasicBlocks.next()
    TotalBlocks = TotalBlocks + 1

    StartAddress = CurrentBlock.getFirstStartAddress()
    if StartAddress is None:
        continue

    CurrentFunction = FunctionManager.getFunctionContaining(StartAddress)
    if CurrentFunction is None:
        continue

    FunctionName = CurrentFunction.getName()

    MemoryOperations, BranchOperations, IndirectBranching, InstructionCount = \
        score_block(CurrentBlock, ProgramListing)

    if InstructionCount == 0:
        continue

    VirtualMachineScore = BranchOperations + MemoryOperations * 2 + (InstructionCount // 2)
    if IndirectBranching: #determines if dispatcher or handler right here
        VirtualMachineScore = VirtualMachineScore + 20

    Classification = None

    if IndirectBranching:
        Classification = "dispatcher_candidate"
    else:
        if (InstructionCount <= HANDLER_SIZE and
            InstructionCount >= MIN_HANDLER and
            MemoryOperations >= MAXIMUM_memoryOperations):
            Classification = "handler_candidate"

    if Classification is None:
        continue

    MaximumAddress = CurrentBlock.getMaxAddress()
    MinimumAddress = CurrentBlock.getMinAddress()
    BlockSize = MaximumAddress.subtract(MinimumAddress) + 1
    BlockSizeInt = int(BlockSize)

    try:
        ByteBuffer = zeros(BlockSizeInt, 'b')
        ProgramMemory.getBytes(MinimumAddress, ByteBuffer)
        RawBytes = bytearray(ByteBuffer)
    except Exception:
        print "read fail"
        continue

    BlockFileName = "vmblock_%03d_%s.bin" % (BlockIdentifier, str(MinimumAddress))
    BlockFilePath = os.path.join(OutputDirectory, BlockFileName)

    try:
        BlockFileHandle = open(BlockFilePath, "wb")
        try:
            BlockFileHandle.write(RawBytes)
        finally:
            BlockFileHandle.close()
        print "saved" #save me from this nightmare
    except Exception:
        print "write fail"
        continue

    OutputLine = (
        "block_id=%d func=%s start=%s end=%s size=%d insts=%d "
        "MemoryOperations=%d BranchOperations=%d indirect=%s score=%d class=%s file=%s"
        % (
            BlockIdentifier,
            FunctionName,
            str(MinimumAddress),
            str(MaximumAddress),
            BlockSizeInt,
            InstructionCount,
            MemoryOperations,
            BranchOperations,
            str(IndirectBranching),
            VirtualMachineScore,
            Classification,
            BlockFileName,
        )
    )

    IndexLines.append(OutputLine)
    RankingEntries.append((VirtualMachineScore, OutputLine))

    BlockIdentifier = BlockIdentifier + 1
    SavedBlocks = SavedBlocks + 1


try:
    IndexFileHandle = open(IndexFilePath, "w")
    try:
        for OutputLine in IndexLines:
            IndexFileHandle.write(OutputLine + "\n")
    finally:
        IndexFileHandle.close()
    print "Index"
except Exception:
    print "Fail"


try:
    RankingEntries.sort(key=lambda EntryTuple: EntryTuple[0], reverse=True)
    RankingFileHandle = open(RankingFilePath, "w")
    try:
        for BlockScore, OutputLine in RankingEntries:
            RankingFileHandle.write("%d\t%s\n" % (BlockScore, OutputLine))
    finally:
        RankingFileHandle.close()
    print "Ranked"
except Exception:
    print "Faiil"
print "Woirked :)"
