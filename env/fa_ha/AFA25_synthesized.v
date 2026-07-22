/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:21:39 2026
/////////////////////////////////////////////////////////////


module AFA25 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n3;

  OR2_X1 U6 ( .A1(b), .A2(cin), .ZN(cout) );
  INV_X1 U7 ( .A(a), .ZN(n3) );
  NOR2_X1 U8 ( .A1(cout), .A2(n3), .ZN(sum) );
endmodule

