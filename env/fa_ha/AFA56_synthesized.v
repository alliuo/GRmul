/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:59:50 2026
/////////////////////////////////////////////////////////////


module AFA56 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;

  assign sum = 1'b1;

  AND2_X1 U5 ( .A1(b), .A2(cin), .ZN(cout) );
endmodule

