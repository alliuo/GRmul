/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:01:57 2026
/////////////////////////////////////////////////////////////


module AFA9 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   a, n4, n5;
  assign cout = a;

  INV_X1 U6 ( .A(a), .ZN(n4) );
  AOI21_X1 U7 ( .B1(cin), .B2(n4), .A(b), .ZN(n5) );
  INV_X1 U8 ( .A(n5), .ZN(sum) );
endmodule

