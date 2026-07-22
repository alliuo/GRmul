/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:00:43 2026
/////////////////////////////////////////////////////////////


module AFA8 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n7, n8, n9, n10;

  INV_X1 U9 ( .A(b), .ZN(n8) );
  AOI21_X1 U10 ( .B1(cin), .B2(n8), .A(a), .ZN(n7) );
  OAI21_X1 U11 ( .B1(cin), .B2(n8), .A(n7), .ZN(sum) );
  INV_X1 U12 ( .A(a), .ZN(n10) );
  NAND2_X1 U13 ( .A1(cin), .A2(b), .ZN(n9) );
  NAND2_X1 U14 ( .A1(n10), .A2(n9), .ZN(cout) );
endmodule

