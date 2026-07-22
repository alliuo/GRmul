/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:37:39 2026
/////////////////////////////////////////////////////////////


module AFA38 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n6, n7, n8;

  AOI21_X1 U8 ( .B1(b), .B2(cin), .A(a), .ZN(n6) );
  INV_X1 U9 ( .A(n6), .ZN(cout) );
  INV_X1 U10 ( .A(cin), .ZN(n8) );
  INV_X1 U11 ( .A(a), .ZN(n7) );
  OAI21_X1 U12 ( .B1(b), .B2(n8), .A(n7), .ZN(sum) );
endmodule

