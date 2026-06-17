interface Submission {
    filename: string;
    name: string;
    // True once the submission has been analyzed (a per-model eval exists).
    // Only analyzed submissions can be exported.
    analyzed: boolean;
}

export default Submission;
