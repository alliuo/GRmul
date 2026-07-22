/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 20:57:01 2026
/////////////////////////////////////////////////////////////


module AFA5 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n5, n6, n7;

  INV_X1 U8 ( .A(a), .ZN(n5) );
  INV_X1 U9 ( .A(cin), .ZN(n7) );
  INV_X1 U10 ( .A(b), .ZN(n6) );
  AOI21_X1 U11 ( .B1(n5), .B2(n7), .A(n6), .ZN(cout) );
  OAI221_X1 U12 ( .B1(b), .B2(n7), .C1(n6), .C2(cin), .A(n5), .ZN(sum) );
endmodule

