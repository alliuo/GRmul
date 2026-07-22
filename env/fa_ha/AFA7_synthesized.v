/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 20:59:29 2026
/////////////////////////////////////////////////////////////


module AFA7 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n4, n5;

  AOI21_X1 U7 ( .B1(cin), .B2(b), .A(a), .ZN(n4) );
  INV_X1 U8 ( .A(n4), .ZN(cout) );
  NOR2_X1 U9 ( .A1(cin), .A2(b), .ZN(n5) );
  NOR2_X1 U10 ( .A1(cout), .A2(n5), .ZN(sum) );
endmodule

