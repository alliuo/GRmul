/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:43:48 2026
/////////////////////////////////////////////////////////////


module AFA43 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n3;

  OR2_X1 U6 ( .A1(a), .A2(b), .ZN(cout) );
  INV_X1 U7 ( .A(cin), .ZN(n3) );
  NOR2_X1 U8 ( .A1(cout), .A2(n3), .ZN(sum) );
endmodule

