/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 20:52:06 2026
/////////////////////////////////////////////////////////////


module AFA1 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n7, n8, n9, n10;

  NOR2_X1 U9 ( .A1(b), .A2(a), .ZN(n8) );
  NAND2_X1 U10 ( .A1(b), .A2(a), .ZN(n10) );
  NAND2_X1 U11 ( .A1(n8), .A2(cin), .ZN(n7) );
  OAI211_X1 U12 ( .C1(n8), .C2(cin), .A(n10), .B(n7), .ZN(sum) );
  OAI21_X1 U13 ( .B1(b), .B2(a), .A(cin), .ZN(n9) );
  NAND2_X1 U14 ( .A1(n10), .A2(n9), .ZN(cout) );
endmodule

