/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:49:58 2026
/////////////////////////////////////////////////////////////


module AFA48 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n5, n6;

  INV_X1 U7 ( .A(a), .ZN(n5) );
  OR3_X1 U8 ( .A1(b), .A2(cin), .A3(n5), .ZN(cout) );
  NAND3_X1 U9 ( .A1(a), .A2(cin), .A3(b), .ZN(n6) );
  NAND2_X1 U10 ( .A1(n6), .A2(cout), .ZN(sum) );
endmodule

