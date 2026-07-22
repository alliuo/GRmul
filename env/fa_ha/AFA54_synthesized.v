/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:57:24 2026
/////////////////////////////////////////////////////////////


module AFA54 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n4, n5;

  OAI21_X1 U7 ( .B1(b), .B2(cin), .A(a), .ZN(n4) );
  INV_X1 U8 ( .A(n4), .ZN(cout) );
  INV_X1 U9 ( .A(b), .ZN(n5) );
  NAND3_X1 U10 ( .A1(a), .A2(cin), .A3(n5), .ZN(sum) );
endmodule

