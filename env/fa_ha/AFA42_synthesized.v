/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:42:33 2026
/////////////////////////////////////////////////////////////


module AFA42 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n5, n6;

  NAND2_X1 U7 ( .A1(a), .A2(cin), .ZN(n5) );
  NAND2_X1 U8 ( .A1(b), .A2(n5), .ZN(sum) );
  INV_X1 U9 ( .A(b), .ZN(n6) );
  NAND2_X1 U10 ( .A1(n6), .A2(n5), .ZN(cout) );
endmodule

