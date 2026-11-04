<%@ page contentType="text/html" pageEncoding="UTF-8" %>
<%@ include file="header.jspf" %>
<h1>Exchange rate</h1>
<p>Enter the name of a currency: dollar, euro, USD, EUR, доллар, евро.</p>
<form name="Currency Input Form" action="rate.jsp">
  Currency:
  <input type="text" name="name" />
  <input type="submit" value="OK" />
</form>
<p class="chips">Try:
  <a href="rate.jsp?name=dollar">dollar</a>
  <a href="rate.jsp?name=euro">euro</a>
  <a href="rate.jsp?name=USD">USD</a>
  <a href="rate.jsp?name=%D0%B5%D0%B2%D1%80%D0%BE">евро</a>
</p>
</main>
</body>
</html>
