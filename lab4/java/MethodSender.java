import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

/**
 * Sends a JSON {"method": "...", "args": [...]} request to the Python reflection bridge.
 */
public class MethodSender {
    public static void main(String[] args) throws Exception {
        String host = args.length > 0 ? args[0] : "127.0.0.1";
        int port = args.length > 1 ? Integer.parseInt(args[1]) : 8010;
        String method = args.length > 2 ? args[2] : "greet";
        String extra = args.length > 3 ? args[3] : "";

        String json;
        if (extra.isEmpty()) {
            json = "{\"method\":\"" + method + "\",\"args\":[]}";
        } else {
            json = "{\"method\":\"" + method + "\",\"args\":[\"" + extra + "\"]}";
        }

        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(host, port), 3000);
            OutputStream out = socket.getOutputStream();
            out.write(json.getBytes(StandardCharsets.UTF_8));
            out.flush();
            socket.shutdownOutput();

            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
            String line = reader.readLine();
            System.out.println(line);
        }
    }
}
