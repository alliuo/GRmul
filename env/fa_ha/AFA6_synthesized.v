/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 20:58:15 2026
/////////////////////////////////////////////////////////////


module AFA6 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n5, n6, n7;

  AOI21_X1 U8 ( .B1(a), .B2(cin), .A(b), .ZN(n5) );
  INV_X1 U9 ( .A(n5), .ZN(cout) );
  INV_X1 U10 ( .A(b), .ZN(n6) );
  NAND2_X1 U11 ( .A1(cin), .A2(n6), .ZN(n7) );
  XNOR2_X1 U12 ( .A(a), .B(n7), .ZN(sum) );
endmodule

