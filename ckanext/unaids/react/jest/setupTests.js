import "regenerator-runtime/runtime";
import '@testing-library/jest-dom/extend-expect';
import { toBeEmpty } from "jest-extended";

expect.extend({ toBeEmpty });
