/*
 * Not using a dependency manager : direct download dependencies (parser and gson) as jar and place it under libs
 *      https://github.com/google/gson/releases?
 *      https://github.com/javaparser/javaparser/releases?
 * Compile this java file from the root : javac -cp "libs/gson-2.10.1.jar:libs/javaparser-core-3.25.4.jar" -d test_out scripts/GenerateAST.java
 * Run : java -cp "test_out:libs/gson-2.10.1.jar:libs/javaparser-core-3.25.4.jar" scripts/GenerateAST java/AssignmentServiceImpl.java
 */

package scripts;

import com.github.javaparser.*;
import com.github.javaparser.ast.*;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.expr.*;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import com.google.gson.*;

import java.io.*;
import java.util.*;

/* References
 * https://www.baeldung.com/javaparser
 * https://javadoc.io/doc/com.github.javaparser/javaparser-core/latest/index.html
 */
public class GenerateAST {

    public static void main(String[] args) throws IOException{
        if(args.length != 1){
            System.err.println("Expected usage is : java GenerateAST <JavaCode_FilePath>'");
            return;
        }

        //Parsing Source Files -> provide a source code and generate a compilationUnit as result
        CompilationUnit parsed = StaticJavaParser.parse(new File(args[0]));

        // Visitor Design Pattern is used to visit the parsed objects contents
        ClassVisitor visitor = new ClassVisitor();
        parsed.accept(visitor, null);

        Map<String, Object> output = new LinkedHashMap<>();
        output.put("package", parsed.getPackageDeclaration().map(pd -> pd.getName().toString()).orElse(""));
        output.put("classes", visitor.getClasses());

        Gson gson = new GsonBuilder().disableHtmlEscaping().setPrettyPrinting().create();
        System.out.println(gson.toJson(output));
    }

    private static class ClassVisitor extends VoidVisitorAdapter<Void>{

        private final List<Map<String, Object>> classes = new ArrayList<>();

        public List<Map<String, Object>> getClasses() {
            return classes;
        }

        /* Collects class-level + method-level info for all classes */
        @Override
        public void visit(ClassOrInterfaceDeclaration cid, Void arg){

            Map<String, Object> classInfo = new LinkedHashMap<>();
            classInfo.put("class", cid.getNameAsString());


            List<Map<String, Object>> methods = new ArrayList<>();

            for (MethodDeclaration md : cid.findAll(MethodDeclaration.class)) {

                Map<String,Object> method = new LinkedHashMap<>();

                // Store the method name
                method.put("name", md.getNameAsString());

                // Store the methods return type
                method.put("returnType",md.getType().asString());

                // Store the parameters of the method
                List<String> params = new ArrayList<>();
                for(Parameter param : md.getParameters()){
                    params.add(param.getType().asString());
                }
                method.put("parameters", params);

                // Store the methods that are called from the current method
                List<String> methodCalls = new ArrayList<>();
                md.findAll(MethodCallExpr.class)
                    .forEach(mc -> {
                        // Check if it is a qualified method call like object.method()
                        if(mc.getScope().isPresent()){
                            methodCalls.add(mc.getScope().get() + "." + mc.getName());
                        }
                        // Or if it is an unqualified method call just as method()
                        else{
                            methodCalls.add(mc.getNameAsString());
                        }
                    });
                method.put("methodCalls",methodCalls);

                // Store the variable declarations local to the method (Having this to help in summary generation on what the method does)
                List<Map<String,String>> methodLocalVariables = new ArrayList<>();
                md.findAll(VariableDeclarator.class)
                    .forEach(vd -> {
                        // Get the variable name and its type
                        Map<String,String> variableInfo = new HashMap<>();
                        variableInfo.put("var_name", vd.getNameAsString());
                        variableInfo.put("var_type",vd.getType().asString());
                        methodLocalVariables.add(variableInfo);
                    }); 
                method.put("methodLocalVariables",methodLocalVariables);

                // Store field access made inside the method body
                List<String> methodFieldAccess = new ArrayList<>();
                md.findAll(FieldAccessExpr.class)
                    .forEach(fa -> {
                        methodFieldAccess.add(fa.getScope() + "." + fa.getName());
                    });
                method.put("methodFieldAccess",methodFieldAccess);

                // Store the actual method body if it is present
                if(md.getBody().isPresent()){
                    method.put("methodBody",md.getBody().get().toString());
                }
                else{
                    method.put("methodBody","");
                }

                methods.add(method);
            }

            List<Map<String, String>> classFields = new ArrayList<>();
            for (FieldDeclaration field : cid.getFields()) {
                for (VariableDeclarator var : field.getVariables()) {
                    Map<String, String> fieldInfo = new HashMap<>();
                    fieldInfo.put("var_name", var.getNameAsString());
                    fieldInfo.put("var_type", var.getType().asString());
                    classFields.add(fieldInfo);
                }
            }
            classInfo.put("classFields", classFields);

            classInfo.put("methods", methods);
            classes.add(classInfo);

            super.visit(cid, arg);
        }

    }
    
}
