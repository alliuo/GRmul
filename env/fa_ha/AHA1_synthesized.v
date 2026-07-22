/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 22:05:57 2026
/////////////////////////////////////////////////////////////


module AHA1 ( a, b, cout, sum );
  input a, b;
  output cout, sum;

  assign cout = 1'b0;

  OR2_X1 U5 ( .A1(a), .A2(b), .ZN(sum) );
endmodule

