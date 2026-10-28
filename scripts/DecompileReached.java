// Decompile only selected ARM functions supported by live traces.
//@category NC3
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import java.nio.file.Files;
import java.nio.file.Path;
import java.math.BigInteger;

public class DecompileReached extends GhidraScript {
    public void run() throws Exception {
        String[] args = getScriptArgs();
        Path output = Path.of(args[0]);
        Files.createDirectories(output);
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        for (int i = 1; i < args.length; ++i) {
            String[] spec = args[i].split(":");
            Address entry = toAddr(Long.parseUnsignedLong(spec[0], 16));
            String name = spec.length > 1 ? spec[1] : "reached_" + spec[0];
            if (getInstructionAt(entry) == null) {
                currentProgram.getProgramContext().setValue(
                    currentProgram.getRegister("TMode"), entry, entry, BigInteger.ZERO);
            }
            disassemble(entry);
            Function function = getFunctionAt(entry);
            if (function == null) function = createFunction(entry, name);
            if (function == null) { printerr("Cannot define " + entry); continue; }
            DecompileResults result = decompiler.decompileFunction(function, 60, monitor);
            String text = "/* Entry " + entry + "; body " + function.getBody() + " */\n";
            if (result.decompileCompleted()) text += result.getDecompiledFunction().getC();
            else text += "/* Decompiler error: " + result.getErrorMessage() + " */\n";
            Files.writeString(output.resolve(name + ".c"), text);
            println("NC3 exported " + name + " at " + entry);
        }
        decompiler.dispose();
    }
}
