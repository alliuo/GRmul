/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:46:16 2026
/////////////////////////////////////////////////////////////


module AFA45 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n5, n6;

  NAND2_X1 U7 ( .A1(a), .A2(cin), .ZN(n5) );
  INV_X1 U8 ( .A(b), .ZN(n6) );
  NAND2_X1 U9 ( .A1(n5), .A2(n6), .ZN(cout) );
  OAI21_X1 U10 ( .B1(n6), .B2(n5), .A(cout), .ZN(sum) );
endmodule

