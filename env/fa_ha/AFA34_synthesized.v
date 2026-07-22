/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:32:42 2026
/////////////////////////////////////////////////////////////


module AFA34 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n2, n3;

  OAI21_X1 U5 ( .B1(a), .B2(cin), .A(b), .ZN(n3) );
  NAND2_X1 U6 ( .A1(a), .A2(cin), .ZN(n2) );
  NAND2_X1 U7 ( .A1(n3), .A2(n2), .ZN(cout) );
  INV_X1 U8 ( .A(cout), .ZN(sum) );
endmodule

