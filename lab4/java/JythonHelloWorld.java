import org.python.util.PythonInterpreter;

/** The opposite direction: Java starts a Jython interpreter and runs Python code in it. */
public class JythonHelloWorld {
    public static void main(String[] args) {
        try (PythonInterpreter python = new PythonInterpreter()) {
            python.exec("print('Hello Python World!')");
            // a pure Python module (lab4/jython/jy10.py), found through -Dpython.path
            python.exec("from jy10 import greet\ngreet('John')");
            // values travel both ways
            python.set("n", 10);
            python.exec("result = n ** 2");
            System.out.println("Python computed n ** 2 = " + python.get("result", Integer.class));
        }
    }
}
