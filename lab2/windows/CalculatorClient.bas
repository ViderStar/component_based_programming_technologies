Attribute VB_Name = "CalculatorClient"
' Excel / Word VBA client for the Python COM server "Lab2.Calculator".
' Alt+F11 -> File -> Import File, then Alt+F8 -> FillSheetFromComServer.

Sub FillSheetFromComServer()
    Dim calc As Object
    Dim ws As Worksheet

    On Error Resume Next
    Set calc = CreateObject("Lab2.Calculator")
    On Error GoTo 0
    If calc Is Nothing Then
        MsgBox "Failed to create COM object. Please ensure it is registered."
        Exit Sub
    End If

    Set ws = ThisWorkbook.Sheets(1)
    ws.Range("A1:E1").Value = Array("a", "op", "b", "result", "COM method")
    ws.Range("A2:E2").Value = Array(2, "+", 3, calc.Add(2, 3), "Lab2.Calculator.Add")
    ws.Range("A3:E3").Value = Array(7, "-", 10, calc.Sub(7, 10), "Lab2.Calculator.Sub")
    ws.Range("A4:E4").Value = Array(6, "*", 7, calc.Mul(6, 7), "Lab2.Calculator.Mul")
    ws.Range("A5:E5").Value = Array(7, "/", 2, calc.Div(7, 2), "Lab2.Calculator.Div")
    ws.Range("A6:E6").Value = Array(2, "^", 10, calc.Pow(2, 10), "Lab2.Calculator.Pow")

    Set calc = Nothing
End Sub

' UserForm button handler, as in the handout.
Private Sub CommandButton1_Click()
    Dim calc As Object
    Set calc = CreateObject("Lab2.Calculator")
    MsgBox "2 ^ 10 = " & calc.Pow(2, 10)
    Set calc = Nothing
End Sub
