# Lab 2: Remote module invocation

## Idea

The client asks another process to run a function it does not have locally. The server loads the module, calls the function, and returns the result. From the client it looks local: `proxy.add(2, 3)`.

## Models

| Protocol | Idea | Transport |
| --- | --- | --- |
| **RPC / XML-RPC** | method + params in an envelope | HTTP |
| **SOAP** | XML + WSDL | HTTP |
| **REST** | resources and HTTP verbs | HTTP |
| **MQTT** | publish to a topic | broker |
| **Java RMI / Pyro** | live objects over the wire | custom |

This lab uses **XML-RPC** from the stdlib: `xmlrpc.server.SimpleXMLRPCServer` and `xmlrpc.client.ServerProxy` (Python client plus a Java class that posts the same XML; no Jython).

## XML-RPC

The client POSTs:

```xml
<methodCall>
  <methodName>add</methodName>
  <params>
    <param><value><int>2</int></value></param>
    <param><value><int>3</int></value></param>
  </params>
</methodCall>
```

The server answers with `<methodResponse>`. Python hides XML behind `ServerProxy`.

Registered methods:

- `add(x, y)`, `mul(x, y)`
- `greet_student(name, group)`
- `inspect_module()` — signatures (link to Lab 4)
- `system.listMethods`

## CGI — theory only

The lecture uses HTML forms and `cgi.FieldStorage`. `cgi` is gone in Python 3.13+. Not implemented here.

## Java client

`lab2/java/XmlRpcClient.java` builds a `methodCall` string and POSTs it with `HttpURLConnection`. No JARs.

## Errors

Missing server, unknown method, type mismatch → XML-RPC fault. The GUI shows the exception. The server runs in a daemon thread and shuts down cleanly.

## Links

- **Lab 1** ships whole objects; XML-RPC serializes arguments as XML.
- **Lab 4** calls a method **by string name** — same idea as `getattr(proxy, method_name)`.
