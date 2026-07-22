/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:03:11 2026
/////////////////////////////////////////////////////////////


module AFA10 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n5, n6, n7;

  NAND2_X1 U8 ( .A1(a), .A2(b), .ZN(n6) );
  NOR2_X1 U9 ( .A1(a), .A2(b), .ZN(n5) );
  AOI21_X1 U10 ( .B1(cin), .B2(n6), .A(n5), .ZN(sum) );
  INV_X1 U11 ( .A(cin), .ZN(n7) );
  NAND2_X1 U12 ( .A1(n7), .A2(n6), .ZN(cout) );
endmodule

