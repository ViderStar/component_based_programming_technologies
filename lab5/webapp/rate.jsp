<%@ page contentType="text/html" pageEncoding="UTF-8" %>
<% request.setCharacterEncoding("UTF-8"); %>
<%@ include file="header.jspf" %>
<jsp:useBean id="currency" scope="session" class="com.CurrencyBean" />
<jsp:setProperty name="currency" property="name" />
<h1>Exchange rate</h1>
<% if (currency.getName() == null) { %>
<p class="error">No currency entered yet.</p>
<% } else if (!currency.isKnown()) { %>
<p class="error">Unknown currency: “<%= currency.getName().replace("&", "&amp;").replace("<", "&lt;") %>”.
Only the dollar and the euro are supported.</p>
<% } else { %>
<p>Currency: <b><jsp:getProperty name="currency" property="title" /></b> (<jsp:getProperty name="currency" property="code" />)</p>
<p class="answer">1 <jsp:getProperty name="currency" property="code" /> = <span id="rate"><jsp:getProperty name="currency" property="rate" /></span> BYN</p>
<p class="muted">Date <jsp:getProperty name="currency" property="date" />,
source: <span id="source"><jsp:getProperty name="currency" property="source" /></span>
(NBRB = National Bank of the Republic of Belarus, table = built-in rates when the bank cannot be reached).</p>
<% } %>
<p><a href="currency.jsp">Another currency</a></p>
</main>
</body>
</html>
