<%@ page contentType="text/html" pageEncoding="UTF-8" %>
<%@ page import="java.util.*" %>
<%@ page import="java.text.SimpleDateFormat" %>
<%@ include file="header.jspf" %>
<%! String getDate() {
        Date dt = new Date();
        return new SimpleDateFormat("dd.MM.yyyy HH:mm:ss").format(dt); } %>
<h1>Hello from JSP</h1>
<hr>
TODAY IS: <%= getDate() %>
<hr>
<p>Lab 5. JSP pages on Apache Tomcat <%= application.getServerInfo().replace("Apache Tomcat/", "") %>,
Java <%= System.getProperty("java.version") %>.</p>
<table>
  <tr><th>#</th><th>Task</th><th>Page</th></tr>
  <tr><td>0</td><td>Prototype of the handout: a form and a session bean</td><td><a href="hello.jsp">hello.jsp</a></td></tr>
  <tr><td>1</td><td>Exchange rate of the dollar and the euro</td><td><a href="currency.jsp">currency.jsp</a></td></tr>
  <tr><td>2</td><td>A JSP page returns a PNG image</td><td><a href="image.html">image.html</a></td></tr>
  <tr><td>3</td><td>English ⇄ Russian translator</td><td><a href="translate.jsp">translate.jsp</a></td></tr>
  <tr><td>4</td><td>A whole site written to <code>response.getWriter()</code></td><td><a href="site.jsp">site.jsp</a></td></tr>
</table>
</main>
</body>
</html>
