/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:30:14 2026
/////////////////////////////////////////////////////////////


module AFA32 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n6, n7, n8;

  OAI21_X1 U8 ( .B1(cin), .B2(b), .A(a), .ZN(n6) );
  NAND2_X1 U9 ( .A1(cin), .A2(b), .ZN(n7) );
  NAND2_X1 U10 ( .A1(n6), .A2(n7), .ZN(cout) );
  INV_X1 U11 ( .A(a), .ZN(n8) );
  OAI21_X1 U12 ( .B1(n8), .B2(n7), .A(cout), .ZN(sum) );
endmodule

