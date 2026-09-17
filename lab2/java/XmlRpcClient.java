import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.nio.charset.StandardCharsets;

/**
 * Minimal XML-RPC client without third-party libraries.
 * Sends a methodCall envelope to the Python SimpleXMLRPCServer.
 */
public class XmlRpcClient {
    public static void main(String[] args) throws Exception {
        String host = args.length > 0 ? args[0] : "127.0.0.1";
        int port = args.length > 1 ? Integer.parseInt(args[1]) : 8000;
        String method = args.length > 2 ? args[2] : "add";
        String left = args.length > 3 ? args[3] : "5";
        String right = args.length > 4 ? args[4] : "3";

        String body = "<?xml version=\"1.0\"?>\n"
                + "<methodCall><methodName>" + method + "</methodName><params>"
                + param(left) + param(right)
                + "</params></methodCall>";

        URI uri = URI.create("http://" + host + ":" + port + "/");
        HttpURLConnection conn = (HttpURLConnection) uri.toURL().openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("Content-Type", "text/xml; charset=utf-8");
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        conn.setRequestProperty("Content-Length", Integer.toString(bytes.length));
        try (OutputStream out = conn.getOutputStream()) {
            out.write(bytes);
        }

        int code = conn.getResponseCode();
        BufferedReader reader = new BufferedReader(new InputStreamReader(
                code >= 400 ? conn.getErrorStream() : conn.getInputStream(),
                StandardCharsets.UTF_8));
        StringBuilder response = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            response.append(line).append('\n');
        }
        reader.close();
        System.out.println("HTTP " + code);
        System.out.println(response);
    }

    private static String param(String raw) {
        try {
            int value = Integer.parseInt(raw);
            return "<param><value><int>" + value + "</int></value></param>";
        } catch (NumberFormatException ignored) {
            return "<param><value><string>" + raw + "</string></value></param>";
        }
    }
}
