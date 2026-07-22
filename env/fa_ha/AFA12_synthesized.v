/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:05:37 2026
/////////////////////////////////////////////////////////////


module AFA12 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n7, n8, n9, n10;

  NOR2_X1 U9 ( .A1(cin), .A2(a), .ZN(n10) );
  INV_X1 U10 ( .A(n10), .ZN(n7) );
  INV_X1 U11 ( .A(b), .ZN(n9) );
  NAND2_X1 U12 ( .A1(cin), .A2(a), .ZN(n8) );
  OAI21_X1 U13 ( .B1(n7), .B2(n9), .A(n8), .ZN(sum) );
  OAI21_X1 U14 ( .B1(n10), .B2(n9), .A(n8), .ZN(cout) );
endmodule

