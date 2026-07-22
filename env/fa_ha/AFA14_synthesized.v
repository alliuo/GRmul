/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:08:05 2026
/////////////////////////////////////////////////////////////


module AFA14 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n5, n6, n7;

  AOI21_X1 U8 ( .B1(b), .B2(a), .A(cin), .ZN(n5) );
  INV_X1 U9 ( .A(n5), .ZN(cout) );
  INV_X1 U10 ( .A(a), .ZN(n7) );
  INV_X1 U11 ( .A(b), .ZN(n6) );
  AOI21_X1 U12 ( .B1(cin), .B2(n7), .A(n6), .ZN(sum) );
endmodule

