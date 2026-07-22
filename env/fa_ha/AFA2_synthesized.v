/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 20:53:20 2026
/////////////////////////////////////////////////////////////


module AFA2 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n3, n4;

  NOR2_X1 U7 ( .A1(a), .A2(b), .ZN(n4) );
  INV_X1 U8 ( .A(cin), .ZN(n3) );
  NOR2_X1 U9 ( .A1(n4), .A2(n3), .ZN(cout) );
  AOI21_X1 U10 ( .B1(n4), .B2(n3), .A(cout), .ZN(sum) );
endmodule

