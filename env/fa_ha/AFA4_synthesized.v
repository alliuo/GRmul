/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 20:55:47 2026
/////////////////////////////////////////////////////////////


module AFA4 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n5, n6, n7;

  NAND2_X1 U8 ( .A1(b), .A2(cin), .ZN(n5) );
  NOR2_X1 U9 ( .A1(a), .A2(n5), .ZN(cout) );
  INV_X1 U10 ( .A(cin), .ZN(n7) );
  AOI21_X1 U11 ( .B1(b), .B2(n7), .A(a), .ZN(n6) );
  OAI21_X1 U12 ( .B1(b), .B2(n7), .A(n6), .ZN(sum) );
endmodule

