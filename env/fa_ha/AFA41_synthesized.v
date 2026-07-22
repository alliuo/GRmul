/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:41:19 2026
/////////////////////////////////////////////////////////////


module AFA41 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   b, n4, n5;
  assign cout = b;

  INV_X1 U6 ( .A(a), .ZN(n5) );
  AOI21_X1 U7 ( .B1(cin), .B2(n5), .A(b), .ZN(n4) );
  OAI21_X1 U8 ( .B1(cin), .B2(n5), .A(n4), .ZN(sum) );
endmodule

