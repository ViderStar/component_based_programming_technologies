<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" trimDirectiveWhitespaces="true" %>
<%@ page import="java.io.*" %>
<%@ page import="java.util.*" %>
<%@ page import="java.text.SimpleDateFormat" %>
<%! String getDate() {
        return new SimpleDateFormat("dd.MM.yyyy HH:mm:ss").format(new Date()); }

    static final String[][] PAGES = {
        {"home", "Home"}, {"labs", "Labs"}, {"tomcat", "Tomcat"}, {"about", "About"},
    };

    static final String[][] LABS = {
        {"1", "Serialization", "pickle, JSON, sockets, WebP"},
        {"2", "COM server", "ProgID, IDispatch, Excel and HTML clients"},
        {"3", "Brython", "Python in the browser, numerical methods"},
        {"4", "Jython", "Java and Python on the JVM, Swing menu"},
        {"5", "JSP", "Tomcat, JavaBeans, an image and a site from JSP"},
    };

    /** The whole site is written by Java code: head, menu, the selected page and the footer. */
    void writeSite(PrintWriter ot, String page, String server) {
        ot.println("<!DOCTYPE html>");
        ot.println("<html lang=\"en\"><head><meta charset=\"UTF-8\">");
        ot.println("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">");
        ot.println("<title>Site from PrintWriter</title>");
        ot.println("<style>");
        ot.println("body{margin:0;font-family:-apple-system,'Segoe UI',Arial,sans-serif;background:#aaeecc;color:#173326}");
        ot.println("header{background:#1d6b4a;color:#fff;padding:18px 24px}header h1{margin:0;font-size:26px}");
        ot.println("nav{display:flex;flex-wrap:wrap;gap:4px;background:#14513a;padding:6px 18px}");
        ot.println("nav a{color:#dff7ea;text-decoration:none;padding:6px 12px;border-radius:6px}nav a.on{background:#2e8a63;color:#fff}");
        ot.println("article{max-width:760px;margin:20px auto;background:#fff;padding:20px 24px;border-radius:10px}");
        ot.println("table{border-collapse:collapse}td,th{border:1px solid #b9dccb;padding:5px 10px;text-align:left}");
        ot.println("footer{text-align:center;color:#2f5b47;font-size:13px;padding:10px}");
        ot.println("</style></head><body>");
        ot.println("<header><h1>Hello programmers all around me!</h1><div>a site sent by <code>response.getWriter()</code></div></header>");
        ot.print("<nav>");
        for (String[] item : PAGES) {
            String on = item[0].equals(page) ? " class=\"on\"" : "";
            ot.print("<a" + on + " href=\"site.jsp?page=" + item[0] + "\">" + item[1] + "</a>");
        }
        ot.print("<a href=\"index.jsp\">&larr; Lab 5</a>");
        ot.println("</nav>");
        ot.println("<article id=\"page-" + page + "\">");
        if (page.equals("labs")) {
            ot.println("<h2>Labs of the course</h2><table><tr><th>#</th><th>Topic</th><th>Keywords</th></tr>");
            for (String[] lab : LABS) {
                ot.println("<tr><td>" + lab[0] + "</td><td>" + lab[1] + "</td><td>" + lab[2] + "</td></tr>");
            }
            ot.println("</table>");
        } else if (page.equals("tomcat")) {
            ot.println("<h2>Server</h2><table>");
            ot.println("<tr><th>Server</th><td>" + server + "</td></tr>");
            ot.println("<tr><th>Java</th><td>" + System.getProperty("java.version") + " (" + System.getProperty("java.vendor") + ")</td></tr>");
            ot.println("<tr><th>OS</th><td>" + System.getProperty("os.name") + " " + System.getProperty("os.arch") + "</td></tr>");
            ot.println("</table>");
        } else if (page.equals("about")) {
            ot.println("<h2>About</h2><p>Component-Based Programming Technologies, BSUIR, 2026.</p>");
            ot.println("<p>Student: Artsem Lebiadzevich. Supervisor: Oleg German.</p>");
        } else {
            ot.println("<h2>Welcome</h2><p>This page has no HTML template: every line comes from <code>ot.println</code>.</p>");
            ot.println("<p>TODAY IS: " + getDate() + "</p>");
        }
        ot.println("</article>");
        ot.println("<footer>Lab 5 &middot; JSP &middot; " + getDate() + "</footer>");
        ot.println("</body></html>");
    }
%>
<%
    String page_ = request.getParameter("page");
    boolean known = false;
    for (String[] item : PAGES) {
        known |= item[0].equals(page_);
    }
    PrintWriter ot = response.getWriter();
    writeSite(ot, known ? page_ : "home", application.getServerInfo());
%>
