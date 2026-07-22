import z3

class PP():
    """
    Partial product
    """
    def __init__(self, name, weight, parents, kind, solver, is_initial=False):
        """
        kind:  0: is sum, 
               1: is cout or initial PP generated using an AND gate,
               2: invert, 
               3: constant 1,
               4: initial PP generated using Booth encoding
               5: negative signal for Booth multiplier
        """
        self.name = name
        self.parents = parents
        self.children = []
        self.graph_idx = None # Index in PP Graph, set when the PP is added.
        
        # Detailed features
        self.level = None
        self.weight = weight
        self.node_type = None # 0: sum,
                              # 1: cout, 
                              # 2: invert, 
                              # 3: constant 1,
                              # 4: initial PP 
        self.adder_output_role = None # 0: sum output of an adder
                                      # 1: cout output of an adder
        self.DIBS = set() # Dependent input bit set

        # z3 solver
        self.solver = solver
        self.var = z3.Bool(name)

        # Update parents and the DIBS.
        if not is_initial: # PP is not at the first level.
            for p in parents:
                p.children.append(self)
                self.DIBS = self.DIBS | p.DIBS
        else:
            self.DIBS = set(self.parents)
            self.DIBS.discard('0') # Exclude constant 0
            self.DIBS.discard('1') # Exclude constant 1.
        
        # Update features.
        if is_initial: # PP is at the first level.
            if kind not in [1, 3, 4, 5]:
                raise ValueError("'kind' must be in [1, 3, 4, 5] for an initial PP.")
            if not all(isinstance(p, str) for p in parents):
                raise ValueError("'parents' must contain strings for an initial PP.")
            if kind == 1 and (len(parents) != 2):
                raise ValueError("There must be two parents.")
            elif kind == 3 and parents != ['1']:
                raise ValueError("Constant 1 can only have one parent '1'")
            elif kind == 4 and (len(parents) not in [3, 5]):
                raise ValueError("Booth-encoded PPs must have 3 or 5 parents")
            elif kind == 5 and (len(parents) not in [2, 3]):
                raise ValueError("negative signal must have 2 or 3 parents")
            
            if kind == 1: # AND.
                self.node_type = 4
                self.level = 1
                p0 = z3.Bool(parents[0])
                p1 = z3.Bool(parents[1])
                self.solver.add(self.var == z3.And(p0, p1))

            elif kind == 3: # Constant 1.
                self.node_type = 3
                self.level = 1
                self.solver.add(self.var == z3.BoolVal(True))

            elif kind == 4: # Booth-encoded PP.
                self.node_type = 4
                self.level = 1
                if len(parents) == 3: # Radix-2 Booth.
                    p0 = z3.Bool(parents[0]) if parents[0] != '0' else z3.BoolVal(False)
                    p1 = z3.Bool(parents[1]) if parents[1] != '0' else z3.BoolVal(False)
                    p2 = z3.Bool(parents[2]) if parents[2] != '0' else z3.BoolVal(False)
                    self.solver.add(self.var == z3.If(p0,
                        z3.If(p1, False, p2),
                        z3.If(p1, z3.Not(p2), False)
                    ))


                else: # Radix-4 Booth.
                    p0 = z3.Bool(parents[0]) if parents[0] != '0' else z3.BoolVal(False)
                    p1 = z3.Bool(parents[1]) if parents[1] != '0' else z3.BoolVal(False)
                    p2 = z3.Bool(parents[2]) if parents[2] != '0' else z3.BoolVal(False)
                    p3 = z3.Bool(parents[3]) if parents[3] != '0' else z3.BoolVal(False)
                    p4 = z3.Bool(parents[4]) if parents[4] != '0' else z3.BoolVal(False)
                    self.solver.add(self.var == z3.If(p2,
                                                    z3.If(p3,
                                                        z3.And(z3.Not(p4), z3.Not(p0)),
                                                        z3.If(p4, 
                                                            z3.Not(p0),
                                                            z3.Not(p1)
                                                        )),
                                                    z3.If(p3,
                                                        z3.If(p4,
                                                            p1,
                                                            p0
                                                        ),
                                                        z3.And(p0, p4)
                                                    )))

            elif kind == 5: # Negative signal for Booth multiplier.
                self.node_type = 4
                self.level = 1
                if len(parents) == 2: # Radix-2 Booth.
                    p0 = z3.Bool(parents[0]) if parents[0] != '0' else z3.BoolVal(False)
                    p1 = z3.Bool(parents[1]) if parents[1] != '0' else z3.BoolVal(False)
                    self.solver.add(self.var == z3.And(p0, z3.Not(p1)))

                else: # Radix-4 Booth.
                    p0 = z3.Bool(parents[0]) if parents[0] != '0' else z3.BoolVal(False)
                    p1 = z3.Bool(parents[1]) if parents[1] != '0' else z3.BoolVal(False)
                    p2 = z3.Bool(parents[2]) if parents[2] != '0' else z3.BoolVal(False)
                    self.solver.add(self.var == z3.And(p0, z3.Not(z3.And(p1, p2))))
        else: # Sum or cout of a half adder.
            if len(parents) != 2:
                raise ValueError("There must be two parents.")
            if kind not in [0, 1]:
                raise ValueError("'kind' must be 0 or 1.")
            self.node_type = kind
            self.adder_output_role = kind # 0: sum, 1: cout.
            self.level = max(parents[0].level, parents[1].level) + 1
            p0 = parents[0].var
            p1 = parents[1].var
            if kind == 0: # Sum.
                self.solver.add(self.var == z3.If(p0, z3.Not(p1), p1))
                
            else: # Cout.
                self.solver.add(self.var == z3.And(p0, p1))
    

    def set_graph_idx(self, idx):
        self.graph_idx = idx


    def take_invert(self):
        if self.node_type not in [0, 1, 4]:
            raise ValueError("only node_type == 0 or 1 or 4 can take invert.")
        self.node_type = 2
        old_var = self.var
        self.var = z3.Bool(self.name + 'n')
        self.solver.add(self.var == z3.Not(old_var))


    def add_parent(self, p):
        if len(self.parents) != 2:
            raise ValueError("Too many parents.")
        self.parents.append(p)
        p.children.append(self)
        self.DIBS = self.DIBS | p.DIBS
        old_var = self.var
        self.var = z3.Bool(self.name + 'new')
        # Update properties.
        self.level = max(self.parents[0].level, self.parents[1].level, self.parents[2].level) + 1
        if self.adder_output_role == 0: # Sum
            self.solver.add(self.var == z3.If(old_var, z3.Not(p.var), p.var))
            
        else:
            p0 = self.parents[0].var
            p1 = self.parents[1].var
            self.solver.add(self.var == z3.If(old_var, 
                                                True, 
                                                z3.If(p.var, 
                                                    z3.If(p0, True, p1),
                                                    False)
                                                ))


    def get_parents_str(self):
        parents_str = []
        for p in self.parents:
            if isinstance(p, str):
                parents_str.append(p)
            else:
                parents_str.append(p.name)
        return parents_str
    

    def get_children_str(self):
        return [c.name for c in self.children]


    def __repr__(self):
        parents_str = self.get_parents_str()
        children_str = self.get_children_str()
        return f"PP(name={self.name!r}, graph_idx={self.graph_idx}, parents={parents_str}, children={children_str}, node_type={self.node_type}, adder_output_role={self.adder_output_role}, weight={self.weight}, level={self.level})"
