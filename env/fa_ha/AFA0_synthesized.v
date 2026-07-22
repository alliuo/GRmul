/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 20:50:53 2026
/////////////////////////////////////////////////////////////


module AFA0 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n5, n6, n7;

  OR2_X1 U8 ( .A1(b), .A2(a), .ZN(n6) );
  AOI22_X1 U9 ( .A1(b), .A2(a), .B1(cin), .B2(n6), .ZN(n5) );
  INV_X1 U10 ( .A(n5), .ZN(cout) );
  NOR2_X1 U11 ( .A1(cin), .A2(n6), .ZN(n7) );
  NOR2_X1 U12 ( .A1(cout), .A2(n7), .ZN(sum) );
endmodule

