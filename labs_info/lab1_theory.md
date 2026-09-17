# Lab 1: Object serialization and deserialization

## Idea

Serialization turns a live Python object into a byte stream (file or socket). Deserialization rebuilds the object. The handout labels this LAB №3; in this repo it is Lab 1.

## pickle

Standard library. Handles most Python objects, including user classes. Open files in binary mode (`wb` / `rb`). On load the class must be importable: pickle stores `module.Class`, not the source.

- `dump` / `dumps` — object → bytes
- `load` / `loads` — bytes → object

The restored instance has the same data, but it is a **new** object.

## JSON

Text format, easy to read and share across languages. Native types: dict, list, str, number, bool, null. `Student` is mapped to a dict by hand. Images are not JSON values — they go as **base64**.

## WebP and base64

wxPython may not open WebP; Pillow decodes the preview.

| Channel | Photo storage |
| --- | --- |
| pickle | `Photo.data: bytes` — raw WebP |
| JSON | `{filename, mime: "image/webp", encoding: "base64", data: "..."}` |
| data URL | `data:image/webp;base64,<payload>` |

JSON grows ~33%. It can be opened in an editor.

## Network

The handout uses `recv(1024)`. Fine for a tiny dict, not for WebP. This lab uses **length-prefix**:

1. 4 bytes length (big-endian `!I`)
2. 8 bytes format name (`pickle` / `json`)
3. payload

The server deserializes `Student` and echoes the same envelope. The “other application” is `python -m lab1.reader artifacts/student.pkl`.

## Visual form

Live wx/tk widgets are not pickled. A **state snapshot** is stored: title, label, button caption, text field. A new window is built from `from_dict`.

## Steps

1. Build `Student(name, group, faculty)`, optionally attach `.webp`.
2. Write pickle and JSON under `artifacts/`.
3. Read them with `lab1.reader`.
4. Start a TCP server, send the object, check the echo.
5. Serialize a GUI form and restore it.
6. Repeat for pickle and JSON.

## Safety

`pickle.loads` of untrusted data can run code. Use JSON at a language boundary. Here both ends are localhost.

## Trade-offs

**pickle**: full Python graph, compact for image bytes. Not human-readable, unsafe, Python-only.

**JSON**: cross-language, easy diffs. Needs a class adapter; images only via base64.

## Links

- **Lab 2** — call a **method** on the server (XML-RPC serializes arguments itself).
- **Lab 4** — pickle restore looks up the class by name (reflection).
