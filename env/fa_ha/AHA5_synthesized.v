/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 22:10:52 2026
/////////////////////////////////////////////////////////////


module AHA5 ( a, b, cout, sum );
  input a, b;
  output cout, sum;
  wire   b;
  assign cout = b;

  INV_X1 U3 ( .A(b), .ZN(sum) );
endmodule

