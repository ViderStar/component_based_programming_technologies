<%@ page contentType="text/html" pageEncoding="UTF-8" %>
<%@ page import="java.util.Map" %>
<% request.setCharacterEncoding("UTF-8"); %>
<%@ include file="header.jspf" %>
<%! String esc(String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;"); } %>
<jsp:useBean id="dictionary" scope="request" class="com.Dictionary" />
<jsp:setProperty name="dictionary" property="word" />
<h1>Translator</h1>
<form name="Word Input Form" action="translate.jsp">
  English or Russian word:
  <input type="text" name="word" value="<%= dictionary.getWord() == null ? "" : esc(dictionary.getWord()) %>" />
  <input type="submit" value="Translate" />
</form>
<% if (dictionary.getWord() != null && !dictionary.getWord().trim().isEmpty()) { %>
  <% if (dictionary.isKnown()) { %>
<p class="answer"><%= esc(dictionary.getWord().trim()) %> → <span id="translation"><jsp:getProperty name="dictionary" property="translation" /></span></p>
<p class="muted">Direction: <span id="direction"><jsp:getProperty name="dictionary" property="direction" /></span></p>
  <% } else { %>
<p class="error" id="unknown">“<%= esc(dictionary.getWord().trim()) %>” is not in the lexicon (<jsp:getProperty name="dictionary" property="direction" />).</p>
  <% } %>
<% } %>
<h3>Lexicon (<%= com.Dictionary.lexicon().size() %> words)</h3>
<p class="chips">
<% for (Map.Entry<String, String> pair : com.Dictionary.lexicon().entrySet()) { %>
  <a href="translate.jsp?word=<%= java.net.URLEncoder.encode(pair.getKey(), "UTF-8") %>"><%= pair.getKey() %></a>
<% } %>
</p>
</main>
</body>
</html>
