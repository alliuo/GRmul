/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:06:50 2026
/////////////////////////////////////////////////////////////


module AFA13 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n6, n7, n8, n9;

  NOR2_X1 U9 ( .A1(a), .A2(b), .ZN(n6) );
  INV_X1 U10 ( .A(cin), .ZN(n8) );
  NAND2_X1 U11 ( .A1(a), .A2(b), .ZN(n7) );
  OAI21_X1 U12 ( .B1(n6), .B2(n8), .A(n7), .ZN(cout) );
  INV_X1 U13 ( .A(n6), .ZN(n9) );
  OAI21_X1 U14 ( .B1(n9), .B2(n8), .A(n7), .ZN(sum) );
endmodule

