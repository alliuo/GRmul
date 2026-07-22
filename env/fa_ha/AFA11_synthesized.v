/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:04:25 2026
/////////////////////////////////////////////////////////////


module AFA11 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n7, n8, n9, n10, n11;

  INV_X1 U10 ( .A(cin), .ZN(n9) );
  NAND2_X1 U11 ( .A1(a), .A2(n9), .ZN(n8) );
  INV_X1 U12 ( .A(a), .ZN(n10) );
  OAI221_X1 U13 ( .B1(cin), .B2(n10), .C1(n9), .C2(a), .A(b), .ZN(n7) );
  OAI21_X1 U14 ( .B1(b), .B2(n8), .A(n7), .ZN(sum) );
  INV_X1 U15 ( .A(b), .ZN(n11) );
  OAI21_X1 U16 ( .B1(n11), .B2(n10), .A(n9), .ZN(cout) );
endmodule

