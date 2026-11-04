<%@ page contentType="text/html" pageEncoding="UTF-8" %>
<% request.setCharacterEncoding("UTF-8"); %>
<%@ include file="header.jspf" %>
<jsp:useBean id="mybean" scope="session" class="com.Hello" />
<jsp:setProperty name="mybean" property="name" />
<h1>Hello, <jsp:getProperty name="mybean" property="name" />!</h1>
<p class="muted">The bean lives in the session: open <a href="response.jsp">response.jsp</a> without a parameter and the name stays.</p>
</main>
</body>
</html>
