; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gemm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.ni = icmp sgt i32 %ni, 0
  br i1 %cmp.ni, label %outer.preheader, label %for.end40

outer.preheader:
  %nj64 = sext i32 %nj to i64
  %nk64 = sext i32 %nk to i64
  %cmp.nj = icmp sgt i32 %nj, 0
  %cmp.nk = icmp sgt i32 %nk, 0
  %ni64 = zext i32 %ni to i64
  br label %for.i

for.i:                                            ; preds = %for.inc38, %outer.preheader
  %i = phi i64 [ 0, %outer.preheader ], [ %inc39, %for.inc38 ]
  %irow = mul nsw i64 %i, %nj64
  %Crow.i = getelementptr inbounds double, ptr %C, i64 %irow
  br i1 %cmp.nj, label %for.j1.preheader, label %for.end.k

for.j1.preheader:
  br label %for.j1

for.j1:                                           ; preds = %for.j1.preheader, %for.j1
  %j1 = phi i64 [ 0, %for.j1.preheader ], [ %inc.j1, %for.j1 ]
  %Cptr1 = getelementptr inbounds double, ptr %Crow.i, i64 %j1
  %cval = load double, ptr %Cptr1, align 8
  %mul = fmul double %cval, %beta
  store double %mul, ptr %Cptr1, align 8
  %inc.j1 = add nuw nsw i64 %j1, 1
  %cmp.j1 = icmp slt i64 %inc.j1, %nj64
  br i1 %cmp.j1, label %for.j1, label %for.end.k

for.end.k:                                        ; preds = %for.j1, %for.i
  %Arow.i = getelementptr inbounds double, ptr %A, i64 %irow
  br i1 %cmp.nk, label %for.k.preheader, label %for.inc38

for.k.preheader:
  br label %for.k

for.k:                                            ; preds = %for.k.preheader, %for.end34
  %k = phi i64 [ 0, %for.k.preheader ], [ %inc36, %for.end34 ]
  %Aptr = getelementptr inbounds double, ptr %Arow.i, i64 %k
  %aval = load double, ptr %Aptr, align 8
  %alpha.aval = fmul double %alpha, %aval
  %krow = mul nsw i64 %k, %nj64
  %Brow.k = getelementptr inbounds double, ptr %B, i64 %krow
  br i1 %cmp.nj, label %for.j2.preheader, label %for.end34

for.j2.preheader:
  br label %for.j2

for.j2:                                           ; preds = %for.j2.preheader, %for.j2
  %j2 = phi i64 [ 0, %for.j2.preheader ], [ %inc.j2, %for.j2 ]
  %Bptr = getelementptr inbounds double, ptr %Brow.k, i64 %j2
  %bval = load double, ptr %Bptr, align 8
  %mul26 = fmul double %alpha.aval, %bval
  %Cptr2 = getelementptr inbounds double, ptr %Crow.i, i64 %j2
  %cval2 = load double, ptr %Cptr2, align 8
  %add31 = fadd double %cval2, %mul26
  store double %add31, ptr %Cptr2, align 8
  %inc.j2 = add nuw nsw i64 %j2, 1
  %cmp.j2 = icmp slt i64 %inc.j2, %nj64
  br i1 %cmp.j2, label %for.j2, label %for.end34

for.end34:                                        ; preds = %for.j2, %for.k
  %inc36 = add nuw nsw i64 %k, 1
  %cmp.k = icmp slt i64 %inc36, %nk64
  br i1 %cmp.k, label %for.k, label %for.inc38

for.inc38:                                        ; preds = %for.end34, %for.end.k
  %inc39 = add nuw nsw i64 %i, 1
  %cmp.i = icmp slt i64 %inc39, %ni64
  br i1 %cmp.i, label %for.i, label %for.end40

for.end40:                                        ; preds = %for.inc38, %entry
  ret void
}

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
