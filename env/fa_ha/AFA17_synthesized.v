/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:11:47 2026
/////////////////////////////////////////////////////////////


module AFA17 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n4, n5;

  OR2_X1 U7 ( .A1(a), .A2(cin), .ZN(cout) );
  INV_X1 U8 ( .A(cin), .ZN(n5) );
  OAI21_X1 U9 ( .B1(a), .B2(n5), .A(b), .ZN(n4) );
  AOI21_X1 U10 ( .B1(a), .B2(n5), .A(n4), .ZN(sum) );
endmodule

