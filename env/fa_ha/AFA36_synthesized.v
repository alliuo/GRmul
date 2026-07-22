/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:35:11 2026
/////////////////////////////////////////////////////////////


module AFA36 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n4;

  OR2_X1 U6 ( .A1(b), .A2(cin), .ZN(cout) );
  INV_X1 U7 ( .A(b), .ZN(n4) );
  NAND2_X1 U8 ( .A1(cin), .A2(n4), .ZN(sum) );
endmodule

