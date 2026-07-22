/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:31:28 2026
/////////////////////////////////////////////////////////////


module AFA33 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n3;

  INV_X1 U6 ( .A(a), .ZN(n3) );
  NAND3_X1 U7 ( .A1(b), .A2(cin), .A3(n3), .ZN(sum) );
  INV_X1 U8 ( .A(sum), .ZN(cout) );
endmodule

