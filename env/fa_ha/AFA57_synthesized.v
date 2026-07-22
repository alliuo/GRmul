/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 22:01:04 2026
/////////////////////////////////////////////////////////////


module AFA57 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n5, n6, n7;

  INV_X1 U8 ( .A(a), .ZN(n5) );
  INV_X1 U9 ( .A(cin), .ZN(n6) );
  INV_X1 U10 ( .A(b), .ZN(n7) );
  AOI21_X1 U11 ( .B1(n5), .B2(n6), .A(n7), .ZN(cout) );
  OAI221_X1 U12 ( .B1(b), .B2(cin), .C1(n7), .C2(n6), .A(a), .ZN(sum) );
endmodule

