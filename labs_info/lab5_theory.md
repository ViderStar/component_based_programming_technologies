# Lab 5: JSP on Tomcat

## Terms

| Term | Meaning |
| --- | --- |
| JSP | Java Server Pages: an HTML page with Java inserts; Tomcat turns it into a servlet and compiles it on the first request |
| Tomcat | a light web server and servlet container (Catalina for servlets, Jasper for JSP) |
| `<%@ page ... %>` | directive: `import`, `contentType`, `pageEncoding`, `trimDirectiveWhitespaces` |
| `<%@ include file="..." %>` | directive: the text of another file is pasted in before compilation |
| `<%! ... %>` | declaration: a field or a method of the generated servlet class |
| `<% ... %>` | scriptlet: Java code inside `_jspService` |
| `<%= ... %>` | expression: its value is written into the page |
| `request`, `response`, `out`, `session`, `application` | implicit objects of every JSP |
| JavaBean | a class with a public no-argument constructor and `getX`/`setX` properties |
| `jsp:useBean`, `jsp:setProperty`, `jsp:getProperty` | create or find a bean in a scope (`page`, `request`, `session`, `application`), fill a property from the request parameter of the same name, print a property |
| WAR | web archive: a jar with JSP/HTML at the root and `WEB-INF/web.xml`, `WEB-INF/classes` inside; `jar -cvf app.war ...` and copy into `webapps/` |

## Life of a JSP

```
browser ── GET /lab5/rate.jsp?name=euro ──► Tomcat (Catalina)
                                              │ first request: Jasper rate.jsp → rate_jsp.java → ecj → rate_jsp.class
                                              ▼
                                   rate_jsp._jspService(request, response)
                                     useBean "currency" in session → setName("euro") → getRate()
                                              │
browser ◄── text/html: 1 EUR = 3.3323 BYN ────┘
```

## The tasks (all in `lab5/webapp/`)

| Page | Task |
| --- | --- |
| `index.jsp` | the handout's `Hello from JSP / TODAY IS:` with `<%! String getDate() %>` |
| `hello.jsp` → `response.jsp` + `com.Hello` | the prototype: a form, a session bean, `Hello, Oleg!` |
| `currency.jsp` → `rate.jsp` + `com.CurrencyBean` | 1. the rate of the dollar and the euro by the name typed in the form |
| `image.html` + `ImageServlet.jsp` | 2. a JSP page answers with `image/png` drawn into a `BufferedImage` |
| `translate.jsp` + `com.Dictionary` | 3. English ⇄ Russian over a limited lexicon |
| `site.jsp` | 4. a whole site written with `PrintWriter ot = response.getWriter()` |

## Things that differ from the handout

- The handout's Tomcat 8.5.5 starts on JDK 17, but its JSP compiler (ecj 4.5.1) cannot read some JDK 17 class files: a page that mentions `System` fails with `ClassFormatException`. Tomcat 8.5.100 (ecj 4.6.3) fails the same way. Tomcat 9 keeps the `javax.servlet` API of the handout and has ecj 4.20, so `scripts/fetch_runtimes.py` downloads 9.0.122.
- In `ImageServlet.jsp` the handout names the stream `OutputStream out`, but `out` is already the implicit `JspWriter`: the page does not compile. The stream is called `os`; `trimDirectiveWhitespaces="true"` keeps the line breaks between directives out of the response, otherwise the writer and the binary stream collide.
- `rate.jsp` keeps the bean in the session, like `response.jsp`: opened without a parameter it shows the last currency.
- Rates come from the National Bank API (`api.nbrb.by`) once a day; without the network (or with `-Dlab5.offline=true`) a built-in table is used, and the page says which.

## Links

- **Lab 3 (Brython)**: the code ran in the browser; here it runs on the server and the browser gets only HTML or PNG.
- **Lab 4 (Jython)**: the same JVM and the same `BufferedImage`/`Graphics2D`, now inside a web server.
