/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 22:13:18 2026
/////////////////////////////////////////////////////////////


module AHA7 ( a, b, cout, sum );
  input a, b;
  output cout, sum;


  NAND2_X1 U5 ( .A1(a), .A2(b), .ZN(sum) );
  INV_X1 U6 ( .A(sum), .ZN(cout) );
endmodule

